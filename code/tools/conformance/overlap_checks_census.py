# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: test-tooling · OS-architecture
# vocabulary (overlap, collision check, contradiction, double-claim, separation of powers, census,
# declared marker, venn2 geometry). NON-GOAL: no offensive capability of any kind — this INSTRUMENT
# reads a record's overlaps (computed from two rules' scopes and declared as venn2 IN relation rows)
# and FEEDS them to the EXISTING collision checks (kernel.views.contradictions /
# handshake_double_claim / separation_of_powers_conflicts, READ and INVOKED, never re-authored),
# censuses the self-declared adoption markers (recognition by policy_key, READ from border.py), and
# names a program-class declared overlap as a finding. It performs no effect, mints no attack, drives
# nothing; it reads records and reuses checks. Full declaration: SCOPE-STATEMENT.md.
"""C6a VT-4 · OVERLAP FEEDS THE CHECKS (the collision checks, the marker census).

design/25 v2.1 rulings 9 & 22, design/53 B8: OVERLAP is NEVER a view node. Where two rules' scopes
are geometry it is COMPUTED (a check at level 4); where they are text it is DECLARED as a venn2 row
(geometry IN, the symmetric non-tree relation). EITHER WAY it FEEDS the existing collision checks —
contradiction, double-claim, concentration (separation of powers) — and a conflict-of-interest is a
CENSUS FINDING, never a new gate check kind (a real gate refusal would be founding). This is the
sibling of the five-families / cell censuses: an INSTRUMENT over records, never a founding op or check
kind.

WHAT IT DOES, over a GIVEN record (store, gate, views) — records are CONTENT, not the op registry, so
unlike its registry-censusing siblings this reads the record it is handed:

  OVERLAP (two readings, one meaning — the two scopes are the SAME GROUND)
      computed : two LIVE rules whose (canonical) scope is equal — a check at level 4 (ruling 22).
      declared : a CREATE-RELATIONSHIP row geometry IN (design/53 B8) — subject~object are one ground.
                 Declared overlaps induce a SCOPE EQUIVALENCE (union-find over the IN rows): two
                 scopes a declared overlap joins collide in the checks below exactly as an equal pair
                 would. THIS is how a declared overlap "feeds" a check — it is the IN row that makes
                 two otherwise-disjoint claims land on one ground.

  FEED THE THREE BUILT COLLISION CHECKS (kernel.views — READ and INVOKED, never re-authored)
      contradiction    : Views.contradictions — same-(a,b,frame) incompatible verdicts.
      double-claim     : handshake_double_claim — two DIFFERENT holders claiming one (stage, scope)
                         (scopes canonicalised through the declared-overlap equivalence first).
      concentration    : separation_of_powers_conflicts — one actor holding all three powers
                         (decision + enforcement + monitoring) for one (canonical) scope.
      A planted overlapping pair that should trip a given check trips EXACTLY it; disjoint scopes
      trip none.

  CONCENTRATION BELOW THRESHOLD — A CENSUS FINDING (A2, first half), never a new gate check kind
      an (actor, scope) where ONE actor holds TWO of the three powers for one (canonical) scope.
      This is the SAME MEASURE as the gate's separation-of-powers refusal (all three) at a LOWER
      threshold, reading NO overlap — it is CONCENTRATION, not conflict of interest (VT-4b renamed
      it `concentration_subthreshold_findings` to name what it measures; archi :3837). STRICTLY
      WEAKER than the all-three refusal: the gate admits two powers (P11 A4 "any two powers pass");
      the census NAMES the two-power holding. It surfaces a concentration; it does not refuse.

  CONFLICT OF INTEREST — THE OVERLAP-FED PAIR MECHANISM (A2, second half; archi :3837), DISTINCT
      an actor holds a POWER (decision/enforcement/monitoring) over rule A's scope AND FALLS INSIDE
      rule B's scope — a subject of B, by its own identity, its group-containment (its ITEM within
      B's scope), or its actor_class (its CLASS within B's scope) — where A and B OVERLAP (their
      scopes are one canonical ground: a computed overlap of equal scopes, or joined by a declared
      IN relation row). THE JUDGE IN ITS OWN CAUSE. Marked OPPOSED where the contradiction
      instrument (Views.contradictions, READ) also names A's and B's scopes incompatible; named
      without the mark otherwise. A DIFFERENT MEASURE from concentration: one power suffices, and
      it reads an OVERLAP the powers count never touches — the two findings are distinct BY MEASURE,
      though one actor may lawfully appear in both for its two different reasons. All inputs READ
      (held stages, rule scopes, the scope equivalence, containment edges, actor_class,
      contradictions); no new source, no founding (a real gate refusal would be founding, STOP (b)).

  THE SELF-DECLARED-MARKER CENSUS (A3)
      the RECOGNISED markers are READ from source (never re-declared here): held_stage
      (Views.HELD_STAGE_KEY), adopts_received_rule (border.ADOPT_MARKER), auto_adopt_parent_rules
      (border.AUTO_ADOPT_MARKER) — recognition by policy_key (border.py:828). Every distinct
      policy_key in the record is read as recognised / MISSPELT-MARKER (a near-miss of a recognised
      marker — a silent miss, a FINDING) / not-a-marker (an ordinary policy key, far from every
      marker). The recognition itself is untouched (STOP condition (d)).

  THE PROGRAM-DECLARED-OVERLAP FINDING (A4)
      a declared-overlap (IN) row whose MINTING ACTOR is PROGRAM-class is a FINDING until stations
      exist (the VT-2 cell cap): a declared overlap carries the JUDGMENT that two grounds overlap,
      and that judgment is a station's step (ruling 9, cell law L28) — a program holds no judgment
      arm. The gate ADMITS the structured row (a program holds the structured arm, cell S), so the
      row lands; the census reads its minter's class and names it. A human- or AI-class declared
      overlap passes.

  OVERLAP STAYS A CHECK, NEVER A NODE (A5)
      no view node is named overlap (design/53 B8): a view_definition named "overlap" is a FINDING,
      and every IN row lands in the NON-TREE band (it is never an actor-tree / item-tree edge — the
      containment reader admits NS/EM only, authority.actor_containment_edges, READ).

USAGE
    python3 -m tools.conformance.overlap_checks_census          # print the census over a demo world
    python3 -m tools.conformance.overlap_checks_census --md     # emit the evidence markdown body

THE DEMO WORLD carries CLEAN rows AND planted findings (a misspelt marker, a program-declared
overlap, a double-claim, an overlap-as-node) so the printed table is watched to REFUSE something — a
census is only proven by a red it produces (the sibling-census discipline).
"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_SRC = os.path.join(os.path.dirname(os.path.dirname(_HERE)), "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from kernel import views as views_module          # noqa: E402  the three built checks + HELD_STAGE_KEY
from kernel import border as border_module         # noqa: E402  the recognised adoption markers
from kernel import authority as authority_module    # noqa: E402  the NS/EM containment reader (READ)

# ---- the venn2 overlap geometry (design/53 B8; founding value_domain {AD, IN, NS, EM}) -----------
# A DECLARED overlap is the SYMMETRIC INTERSECTING geometry IN — named in ONE place, read by both the
# tool and its test. AD (touching), NS/EM (containment) are the other three; only IN is an overlap.
OVERLAP_GEOMETRY = "IN"

# ---- the recognised self-declared markers: READ FROM SOURCE, never re-declared here -------------
# recognition by policy_key (border.py:828 / views.py:1688). A second copy would be a second law; the
# census reads the constants so a rename at the source is a rename here (stop condition (d): read, not
# change).
RECOGNISED_MARKERS = frozenset({
    views_module.Views.HELD_STAGE_KEY,     # "held_stage"          — the stage-holding self-declaration
    border_module.ADOPT_MARKER,            # "adopts_received_rule" — an adoption cites the received rule
    border_module.AUTO_ADOPT_MARKER,       # "auto_adopt_parent_rules" — a standing auto-adopt scope
})

# ---- the three powers (READ from views: the separation-of-powers triad) --------------------------
THREE_POWERS = views_module.THREE_POWERS   # ("decision", "enforcement", "monitoring")

PROGRAM_CLASS = views_module.Views.PROGRAM_ACTOR_CLASS   # "program"

# a misspelt marker is a policy_key within this edit distance of a recognised marker but not equal to
# one (a near-miss that will silently never be recognised). An ordinary policy key is far from every
# marker and is not a finding.
_MISSPELL_MAX_DISTANCE = 2


# =================================================================================================
# OVERLAP — the two readings (computed from scopes, declared as an IN row) and the scope equivalence
# =================================================================================================

def _levenshtein(a, b):
    """The edit distance between two strings (pure; the marker census's near-miss reading)."""
    if a == b:
        return 0
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def declared_overlaps(store, as_of=None):
    """Every DECLARED overlap — a CREATE-RELATIONSHIP row geometry IN (design/53 B8). Returns
    {subject, object, minter, seq} rows, latest-wins per identity NOT applied (a census reads every
    declared row; supersession is old_relationships' concern). `minter` is the RECORDED acting actor
    of the create event (e['actor']) — the class the program-declared-overlap finding reads."""
    out = []
    for e in store.by_action("CREATE-RELATIONSHIP", as_of):
        p = e.get("payload") or {}
        if p.get("geometry") != OVERLAP_GEOMETRY:
            continue
        out.append({"subject": p.get("subject"), "object": p.get("object"),
                    "minter": e.get("actor"), "seq": e.get("seq")})
    return out


def scope_equivalence(store, as_of=None):
    """UNION-FIND over the declared overlaps: subject~object are the SAME GROUND. Returns a function
    canonicalize(scope) -> representative. A scope no declared overlap touches is its own
    representative, so a COMPUTED overlap (equal scope strings) is unaffected — the equivalence only
    JOINS grounds a declared IN row says overlap. This is how a declared overlap FEEDS the checks."""
    parent = {}

    def find(x):
        parent.setdefault(x, x)
        root = x
        while parent[root] != root:
            root = parent[root]
        while parent[x] != root:
            parent[x], x = root, parent[x]
        return root

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            # deterministic representative: the smaller string, so canonicalisation is stable
            lo, hi = sorted((ra, rb), key=lambda s: (s is None, s))
            parent[hi] = lo

    for rel in declared_overlaps(store, as_of):
        s, o = rel["subject"], rel["object"]
        if s is not None and o is not None:
            union(s, o)

    return lambda scope: find(scope) if scope in parent else scope


def computed_scope_overlaps(store, views, as_of=None):
    """COMPUTED overlaps: pairs of LIVE rules whose (canonical) scope is equal — a check at level 4
    (ruling 22). Reads active_rules (READ), canonicalises each rule's scope through the declared-
    overlap equivalence, and pairs rules that share one ground. Returns {a, b, scope} rows."""
    canon = scope_equivalence(store, as_of)
    by_scope = {}
    for rid, r in views.active_rules(as_of).items():
        scope = r.get("scope")
        if scope is None:
            continue
        by_scope.setdefault(canon(scope), []).append(rid)
    out = []
    for scope, rids in by_scope.items():
        rids = sorted(rids)
        for i in range(len(rids)):
            for j in range(i + 1, len(rids)):
                out.append({"a": rids[i], "b": rids[j], "scope": scope})
    return out


# =================================================================================================
# FEED THE THREE BUILT COLLISION CHECKS — kernel.views, READ and INVOKED, never re-authored
# =================================================================================================

def contradiction_hits(views, as_of=None):
    """CONTRADICTION fed by overlap: same-(a,b,frame) incompatible verdicts. REUSES the built
    Views.contradictions (READ, never re-authored). Returns its rows [{a, b, frame, verdicts}]."""
    return views.contradictions(as_of)


def _held_by_holder(store, views, as_of=None):
    """held_stages grouped by HOLDER, scopes CANONICALISED through the declared-overlap equivalence:
    {holder: {(stage, canonical_scope), ...}}. The canonicalisation is what lets a declared overlap
    make two disjoint-looking scopes collide in the double-claim check."""
    canon = scope_equivalence(store, as_of)
    by_holder = {}
    for h in views.held_stages(as_of):
        by_holder.setdefault(h["actor"], set()).add((h["stage"], canon(h["scope"])))
    return by_holder


def double_claim_hits(store, views, as_of=None):
    """DOUBLE-CLAIM fed by overlap: two DIFFERENT holders claiming one (stage, canonical scope).
    REUSES the built handshake_double_claim (READ) — each holder's set is one machine's presentation,
    and the built check intersects two presentations. Returns a sorted list of (stage, scope)."""
    by_holder = _held_by_holder(store, views, as_of)
    holders = sorted(by_holder)
    hits = set()
    for i in range(len(holders)):
        for j in range(i + 1, len(holders)):
            hits |= views_module.handshake_double_claim(by_holder[holders[i]], by_holder[holders[j]])
    return sorted(hits, key=lambda x: (str(x[0]), str(x[1])))


def _canonical_held(store, views, as_of=None):
    """held_stages with each scope CANONICALISED — the presentation the concentration / conflict-of-
    interest readings run over (a declared overlap joins two grounds into one for the powers count)."""
    canon = scope_equivalence(store, as_of)
    return [{"actor": h["actor"], "stage": h["stage"], "scope": canon(h["scope"])}
            for h in views.held_stages(as_of)]


def concentration_hits(store, views, as_of=None):
    """CONCENTRATION (separation of powers) fed by overlap: one actor holding ALL THREE powers for one
    (canonical) scope. REUSES the built separation_of_powers_conflicts (READ). Returns sorted
    (actor, scope) pairs."""
    conflicts = views_module.separation_of_powers_conflicts(_canonical_held(store, views, as_of))
    return sorted(conflicts, key=lambda x: (str(x[0]), str(x[1])))


def concentration_subthreshold_findings(store, views, as_of=None):
    """A2 (first half; VT-4b RENAME of the census's former conflict_of_interest reading — archi
    :3837) — CONCENTRATION BELOW THE REFUSAL THRESHOLD: an (actor, scope) where one actor holds TWO
    of the three powers (decision/enforcement/monitoring) for one (canonical) scope. This is the SAME
    MEASURE as the gate's separation-of-powers refusal (concentration_hits, all three) at a LOWER
    threshold, and reads NO overlap — so it is CONCENTRATION, NOT conflict of interest (that is the
    distinct pair mechanism, conflict_of_interest_findings). STRICTLY WEAKER than the all-three
    refusal: the gate admits two powers (P11 A4 "any two powers pass"), the census NAMES them.
    Returns [{actor, scope, powers}] rows."""
    by_actor_scope = {}
    for h in _canonical_held(store, views, as_of):
        if h["stage"] in THREE_POWERS:
            by_actor_scope.setdefault((h["actor"], h["scope"]), set()).add(h["stage"])
    out = []
    for (actor, scope), powers in by_actor_scope.items():
        if len(powers) >= 2:
            out.append({"actor": actor, "scope": scope, "powers": sorted(powers)})
    return sorted(out, key=lambda r: (str(r["actor"]), str(r["scope"])))


def _actor_containment_ancestors(store, as_of=None):
    """Each actor's group-ancestors (transitive) — READ from the actor-tree containment edges
    (authority.actor_containment_edges, NS/EM, READ never re-authored). {actor: {ancestor groups}}.
    The "item within a scope" reading of the pair mechanism: an actor whose group-ancestor is a
    rule's scope FALLS INSIDE that scope. A DAG walk with a seen-set (cycles refuse at creation)."""
    parents = {}
    for subj, obj in authority_module.actor_containment_edges(store, as_of):
        parents.setdefault(subj, []).append(obj)
    ancestors = {}
    for actor in parents:
        out, seen, stack = set(), set(), list(parents[actor])
        while stack:
            node = stack.pop()
            if node in seen:
                continue
            seen.add(node)
            out.add(node)
            stack.extend(parents.get(node, []))
        ancestors[actor] = out
    return ancestors


def conflict_of_interest_findings(store, views, as_of=None):
    """A2 (second half; VT-4b REBUILD on the OVERLAP-FED PAIR MECHANISM — archi :3837) — CONFLICT OF
    INTEREST, DISTINCT from concentration: an actor holds a POWER (decision/enforcement/monitoring)
    over rule A's scope AND FALLS INSIDE rule B's scope — a subject of B, by its own identity, its
    group-containment (its ITEM within B's scope), or its actor_class (its CLASS within B's scope) —
    where A and B OVERLAP (their scopes are one canonical ground: a computed overlap of equal scopes,
    or joined by a declared IN relation row through the scope equivalence). THIS IS THE JUDGE IN ITS
    OWN CAUSE.

    A DIFFERENT MEASURE from concentration (concentration_subthreshold_findings counts the powers one
    actor holds over one scope, reading NO overlap): here a SINGLE power suffices, and two powers with
    no overlapping rule the actor is inside is NOT a conflict (it is concentration only). Distinct BY
    MEASURE, not disjoint by population — one actor may lawfully appear in BOTH findings, for its two
    DIFFERENT reasons (two powers over S1; AND inside an overlapping rule's scope). The defect the
    separating controls guard is a conflict finding derivable from the POWERS COUNT ALONE.

    Marked OPPOSED where the contradiction instrument (Views.contradictions, READ) also names A's and
    B's scopes incompatible (a same-frame incompatible verdict on the {power_scope, inside_scope}
    pair); named WITHOUT the mark otherwise. Every input is READ (held_stages, active_rules' scopes,
    the scope equivalence, the containment edges, accounts' actor_class, contradictions) — no new
    source, no founding. Returns [{actor, power, power_scope, inside_scope, opposed}] rows."""
    canon = scope_equivalence(store, as_of)
    accounts = views.accounts(as_of)
    ancestors = _actor_containment_ancestors(store, as_of)
    rules = views.active_rules(as_of)
    opposed_pairs = {frozenset((c["a"], c["b"])) for c in views.contradictions(as_of)}

    def falls_inside(actor, scope):
        if actor == scope:
            return True                                    # B's scope names the actor itself (its item)
        if scope in ancestors.get(actor, ()):
            return True                                    # the actor's ITEM is within B's scope (containment)
        if (accounts.get(actor) or {}).get("actor_class") == scope:
            return True                                    # the actor's CLASS is within B's scope
        return False

    out, seen = [], set()
    for h in views.held_stages(as_of):
        if h["stage"] not in THREE_POWERS:
            continue
        actor, a_scope = h["actor"], h["scope"]            # rule A: the actor holds a power over a_scope
        ground = canon(a_scope)
        for r in rules.values():
            b_scope = r.get("scope")
            if b_scope is None:
                continue
            if canon(b_scope) != ground:                   # A and B OVERLAP — one canonical ground
                continue
            if not falls_inside(actor, b_scope):           # the actor is a SUBJECT of B
                continue
            key = (actor, h["stage"], a_scope, b_scope)
            if key in seen:
                continue
            seen.add(key)
            out.append({"actor": actor, "power": h["stage"], "power_scope": a_scope,
                        "inside_scope": b_scope,
                        "opposed": frozenset((a_scope, b_scope)) in opposed_pairs})
    return sorted(out, key=lambda r: (str(r["actor"]), str(r["power_scope"]),
                                      str(r["inside_scope"]), str(r["power"])))


# =================================================================================================
# THE SELF-DECLARED-MARKER CENSUS (A3) — recognition READ from source, a misspelt marker a FINDING
# =================================================================================================

def marker_census(store, as_of=None):
    """Every distinct policy_key in the record, read as recognised / misspelt-marker (a FINDING) /
    not-a-marker. RECOGNISED_MARKERS is READ from source (never re-declared). A misspelt marker is a
    near-miss (edit distance 1..%d) of a recognised marker — a silent miss it never gets recognised
    as. Returns {'recognised': [...], 'misspelt': [{key, nearest, distance}], 'not_a_marker': [...]}.
    """ % _MISSPELL_MAX_DISTANCE
    keys = set()
    for e in store.by_action("CREATE-RULE", as_of):
        pk = (e.get("payload") or {}).get("policy_key")
        if pk is not None:
            keys.add(pk)
    recognised, misspelt, not_a_marker = [], [], []
    for key in sorted(keys):
        if key in RECOGNISED_MARKERS:
            recognised.append(key)
            continue
        nearest, dist = None, None
        for m in RECOGNISED_MARKERS:
            d = _levenshtein(key, m)
            if dist is None or d < dist:
                nearest, dist = m, d
        if 0 < dist <= _MISSPELL_MAX_DISTANCE:
            misspelt.append({"key": key, "nearest": nearest, "distance": dist})
        else:
            not_a_marker.append(key)
    return {"recognised": sorted(recognised), "misspelt": misspelt, "not_a_marker": not_a_marker}


# =================================================================================================
# THE PROGRAM-DECLARED-OVERLAP FINDING (A4)
# =================================================================================================

def program_declared_overlap_findings(store, views, as_of=None):
    """A4 — a declared-overlap (IN) row whose MINTING ACTOR is PROGRAM-class is a FINDING until
    stations exist (the VT-2 cell cap): the overlap JUDGMENT is a station's step, and a program holds
    no judgment arm. Reads the minter's class off accounts() (READ). A human- or AI-class declared
    overlap is NOT flagged (passes). Returns [{subject, object, minter, minter_class, seq}]."""
    accounts = views.accounts(as_of)
    out = []
    for rel in declared_overlaps(store, as_of):
        klass = (accounts.get(rel["minter"]) or {}).get("actor_class")
        if klass == PROGRAM_CLASS:
            out.append({**rel, "minter_class": klass})
    return sorted(out, key=lambda r: r["seq"])


# =================================================================================================
# OVERLAP STAYS A CHECK, NEVER A NODE (A5)
# =================================================================================================

def overlap_node_findings(store, views, as_of=None):
    """A5 — no view node is named overlap (design/53 B8). A view_definition whose name is 'overlap'
    (case-insensitive) is a FINDING. Belt: every declared IN row lands in the NON-TREE band — it is
    never an actor-tree edge (authority.actor_containment_edges admits NS/EM only, READ). Returns
    {'named_nodes': [names], 'in_rows_as_tree_edges': [(subj, obj)]} (both empty is the invariant)."""
    named = [d["name"] for d in views.view_definitions(as_of).values()
             if str(d.get("name")).lower() == "overlap"]
    # an IN row must never be an actor-tree (containment) edge — the reader only admits NS/EM, so this
    # is empty by construction; a non-empty set would mean an overlap was promoted to a tree node.
    containment = set(authority_module.actor_containment_edges(store, as_of))
    in_pairs = {(r["subject"], r["object"]) for r in declared_overlaps(store, as_of)}
    leaked = sorted(in_pairs & containment)
    return {"named_nodes": sorted(named), "in_rows_as_tree_edges": leaked}


# =================================================================================================
# THE CENSUS — assemble every reading over one record; `findings` is the RED set
# =================================================================================================

def census(store, gate, views, as_of=None):
    """One census over a GIVEN record. Returns every reading plus a flat `findings` (the RED set): a
    non-empty findings list is the census refusing something (a misspelt marker, a program-declared
    overlap, an overlap-as-node). The collision-check hits are reported separately (they are the
    checks overlap FEEDS, not census defects)."""
    marker = marker_census(store, as_of)
    program = program_declared_overlap_findings(store, views, as_of)
    nodes = overlap_node_findings(store, views, as_of)
    findings = []
    for m in marker["misspelt"]:
        findings.append({"kind": "misspelt-marker", "detail": m})
    for p in program:
        findings.append({"kind": "program-declared-overlap", "detail": p})
    for n in nodes["named_nodes"]:
        findings.append({"kind": "overlap-as-node", "detail": {"view_name": n}})
    for pair in nodes["in_rows_as_tree_edges"]:
        findings.append({"kind": "overlap-as-tree-edge", "detail": {"pair": pair}})
    return {
        "computed_overlaps": computed_scope_overlaps(store, views, as_of),
        "declared_overlaps": declared_overlaps(store, as_of),
        "contradiction_hits": contradiction_hits(views, as_of),
        "double_claim_hits": double_claim_hits(store, views, as_of),
        "concentration_hits": concentration_hits(store, views, as_of),
        "concentration_subthreshold": concentration_subthreshold_findings(store, views, as_of),
        "conflict_of_interest": conflict_of_interest_findings(store, views, as_of),
        "marker_census": marker,
        "program_declared_overlaps": program,
        "overlap_node_findings": nodes,
        "findings": findings,
    }


# ---- the evidence table (a persisted artifact, the sibling-census idiom) -------------------------

def render_markdown(result):
    out = []
    out.append("<!-- GENERATED by tools/conformance/overlap_checks_census.py — do not hand-edit. -->")
    out.append("<!-- Regenerate: python3 -m tools.conformance.overlap_checks_census --md -->")
    out.append("")
    out.append("# C6a VT-4 · Overlap feeds the checks — the collision checks, the marker census")
    out.append("")
    out.append("Overlap is NEVER a view node (design/25 rulings 9 & 22, design/53 B8). Computed from "
               "two rules' scopes it is a check at level 4; declared as a venn2 IN row it is a "
               "non-tree relation. Either way it FEEDS the existing collision checks — contradiction, "
               "double-claim, concentration — and a conflict-of-interest is a census finding, never a "
               "new gate check kind. This table is the census's reading of one record (the demo "
               "world below carries planted findings so the census is watched to refuse something).")
    out.append("")
    out.append("Computed overlaps: **%d**. Declared overlaps: **%d**. "
               "Contradiction hits: **%d**. Double-claim hits: **%d**. Concentration hits: **%d**. "
               "Concentration (sub-threshold) findings: **%d**. Conflict-of-interest findings: "
               "**%d**. Marker findings (must be watched): **%d**. "
               "Program-declared overlaps: **%d**. Overlap-as-node findings: **%d**." % (
                   len(result["computed_overlaps"]), len(result["declared_overlaps"]),
                   len(result["contradiction_hits"]), len(result["double_claim_hits"]),
                   len(result["concentration_hits"]), len(result["concentration_subthreshold"]),
                   len(result["conflict_of_interest"]),
                   len(result["marker_census"]["misspelt"]),
                   len(result["program_declared_overlaps"]),
                   len(result["overlap_node_findings"]["named_nodes"]),
               ))
    out.append("")

    out.append("## overlaps fed to the checks")
    out.append("")
    out.append("Computed overlaps are rule pairs sharing one canonical ground; a sample is shown "
               "(the count above is the whole set — the founding constitution shares many scopes, "
               "e.g. space:root). Declared overlaps are the venn2 IN rows.")
    out.append("")
    out.append("| kind | a | b | scope |")
    out.append("|---|---|---|---|")
    for o in result["computed_overlaps"][:15]:
        out.append("| computed | %s | %s | %s |" % (o["a"], o["b"], o["scope"]))
    if len(result["computed_overlaps"]) > 15:
        out.append("| ... | ... | ... | (%d computed overlaps total) |" % len(result["computed_overlaps"]))
    for o in result["declared_overlaps"]:
        out.append("| declared (IN) | %s | %s | (minter %s) |" % (o["subject"], o["object"], o["minter"]))
    out.append("")

    out.append("## collision-check hits (the checks overlap feeds — READ from kernel.views)")
    out.append("")
    out.append("| check | hit |")
    out.append("|---|---|")
    for c in result["contradiction_hits"]:
        out.append("| contradiction | %s vs %s @ frame %s: %s |" % (c["a"], c["b"], c["frame"], c["verdicts"]))
    for (stage, scope) in result["double_claim_hits"]:
        out.append("| double-claim | %s @ %s (two holders) |" % (stage, scope))
    for (actor, scope) in result["concentration_hits"]:
        out.append("| concentration | %s @ %s (all three powers) |" % (actor, scope))
    for r in result["concentration_subthreshold"]:
        out.append("| concentration (sub-threshold, finding) | %s @ %s holds %s |"
                   % (r["actor"], r["scope"], r["powers"]))
    for r in result["conflict_of_interest"]:
        out.append("| conflict-of-interest (finding) | %s holds %s over %s, inside %s%s |"
                   % (r["actor"], r["power"], r["power_scope"], r["inside_scope"],
                      " — OPPOSED" if r["opposed"] else ""))
    out.append("")

    out.append("## the self-declared-marker census (recognition READ from border.py:828)")
    out.append("")
    mc = result["marker_census"]
    out.append("Recognised: %s. Not-a-marker: %d ordinary policy keys." % (
        ", ".join(mc["recognised"]) or "none", len(mc["not_a_marker"])))
    out.append("")
    out.append("| policy_key | reading |")
    out.append("|---|---|")
    for m in mc["misspelt"]:
        out.append("| %s | MISSPELT MARKER — near-miss of %s (distance %d), a silent miss |"
                   % (m["key"], m["nearest"], m["distance"]))
    if not mc["misspelt"]:
        out.append("| _none_ | no misspelt marker in this record |")
    out.append("")

    out.append("## the red set — findings the census refuses (must be watched to fire)")
    out.append("")
    out.append("| kind | detail |")
    out.append("|---|---|")
    for f in result["findings"]:
        out.append("| %s | %s |" % (f["kind"], f["detail"]))
    if not result["findings"]:
        out.append("| _none_ | this record is clean |")
    out.append("")
    return "\n".join(out)


EVIDENCE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(_HERE)),
    "planning", "evidence", "VT-4-OVERLAP-CHECKS", "overlap-checks.md")


# ---- a demonstration world: clean rows AND planted findings (watched to refuse something) --------

def _demo_world():
    """A throwaway kernel carrying CLEAN rows and PLANTED findings so the census produces a red — a
    census is proven only by a red it produces. Measurement only; nothing is driven."""
    import tempfile
    from kernel.compose import build_full_kernel
    d = tempfile.mkdtemp(prefix="vt4-census-")
    store, gate, views = build_full_kernel(
        os.path.join(d, "record.jsonl"), os.path.join(d, "blobs"), os.path.join(d, "vault"))[:3]

    # a clean recognised marker (held_stage), an ordinary policy key, and a PLANTED misspelt marker
    gate.execute("CREATE-RULE", "owner", {"rule_id": "H1", "policy_key": "held_stage",
                                          "value": "decision", "scope": "fisheries", "text": "gov-a"})
    gate.execute("CREATE-RULE", "owner", {"rule_id": "B1", "policy_key": "budget:gov-a", "value": 10})
    gate.execute("CREATE-RULE", "owner", {"rule_id": "MIS", "policy_key": "adopts_received_rulle",
                                          "value": "x"})   # PLANTED misspelt marker (one extra l)

    # a PLANTED double-claim: a second holder claims decision @ fisheries
    gate.execute("CREATE-RULE", "owner", {"rule_id": "H2", "policy_key": "held_stage",
                                          "value": "decision", "scope": "fisheries", "text": "gov-b"})

    # a PLANTED program-declared overlap: a program-class actor mints a geometry-IN relation row
    gate.execute("CREATE-ACCOUNT", "owner", {"account_id": "prog1", "actor_class": "program"})
    gate.execute("CREATE-RELATIONSHIP", "prog1", {"subject": "coast", "object": "shore", "geometry": "IN"})

    # a PLANTED overlap-as-node: a view_definition named "overlap"
    gate.execute("CREATE-VIEW", "owner", {"name": "overlap", "when": {"action": "NOOP"},
                                          "then": {"move_to": "Q"}})
    return store, gate, views


def main(argv=None):
    argv = list(argv if argv is not None else sys.argv[1:])
    store, gate, views = _demo_world()
    result = census(store, gate, views)
    if "--md" in argv:
        print(render_markdown(result))
        return 0
    print("computed overlaps %d; declared overlaps %d; contradiction %d; double-claim %d; "
          "concentration %d; concentration-subthreshold %d; conflict-of-interest %d; marker "
          "findings %d; program-declared %d; overlap-as-node %d; TOTAL findings %d" % (
              len(result["computed_overlaps"]), len(result["declared_overlaps"]),
              len(result["contradiction_hits"]), len(result["double_claim_hits"]),
              len(result["concentration_hits"]), len(result["concentration_subthreshold"]),
              len(result["conflict_of_interest"]),
              len(result["marker_census"]["misspelt"]), len(result["program_declared_overlaps"]),
              len(result["overlap_node_findings"]["named_nodes"]), len(result["findings"])))
    for f in result["findings"]:
        print("  FINDING %-24s %s" % (f["kind"], f["detail"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
